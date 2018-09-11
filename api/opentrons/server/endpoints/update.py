import logging
import asyncio
import os
import opentrons
from aiohttp import web
from opentrons import robot
from opentrons import modules

log = logging.getLogger(__name__)


async def _update_firmware(filename, loop):
    """
    This method remains in the API currently because of its use of the robot
    singleton's copy of the driver. This should move to the server lib project
    eventually and use its own driver object (preferably involving moving the
    drivers themselves to the serverlib)
    """
    # ensure there is a reference to the port
    if not robot.is_connected():
        robot.connect()

    # get port name
    port = str(robot._driver.port)
    # set smoothieware into programming mode
    robot._driver._smoothie_programming_mode()
    # close the port so other application can access it
    robot._driver._connection.close()

    # run lpc21isp, THIS WILL TAKE AROUND 1 MINUTE TO COMPLETE
    update_cmd = 'lpc21isp -wipe -donotstart {0} {1} {2} 12000'.format(
        filename, port, robot.config.serial_speed)
    proc = await asyncio.create_subprocess_shell(
        update_cmd,
        stdout=asyncio.subprocess.PIPE,
        loop=loop)
    rd = await proc.stdout.read()
    res = rd.decode().strip()
    await proc.wait()

    # re-open the port
    robot._driver._connection.open()
    # reset smoothieware
    robot._driver._smoothie_reset()
    # run setup gcodes
    robot._driver._setup()

    return res


async def update_module_firmware(request):
    """
     This handler accepts a POST request with Content-Type: multipart/form-data
     and a file field in the body named "module_firmware". The file should
     be a valid HEX image to be flashed to the atmega32u4. The received file is
     sent via USB to the board and flashed by the avr109 bootloader. The file
     is then deleted and a success code is returned
    """
    log.debug('Update Firmware request received')
    data = await request.post()
    module_serial = request.match_info['serial']

    res = await _update_module_firmware(module_serial,
                                        data['module_firmware'],
                                        request.loop)
    if 'successful' not in res['result']:
        if 'avrdude_response' in res and \
                'checksum mismatch' in res['avrdude_response']:
                status = 400
        else:
            status = 500
        log.error(res)
    else:
        status = 200
        log.info(res)
    return web.json_response(res, status=status)


async def _update_module_firmware(module_serial, data, loop=None):

    fw_filename = data.filename
    log.info('Preparing to flash firmware image {}'.format(
        fw_filename))
    content = data.file.read()

    with open(fw_filename, 'wb') as wf:
        wf.write(content)

    config_file_path = os.path.join(opentrons.HERE,
                                    'config', 'modules', 'avrdude.conf')

    # returns a dict of 'Result' & 'AVRDude_response'
    msg = await _upload_to_module(module_serial, fw_filename,
                                  config_file_path, loop=loop)
    log.info('Firmware update complete')
    try:
        os.remove(fw_filename)
    except OSError:
        pass
    # Add firmware filename to response message
    msg['filename'] = fw_filename
    return msg


async def _upload_to_module(serialnum, fw_filename, config_file_path, loop):
    """
    This method remains in the API currently because of its use of the robot
    singleton's copy of the api object & driver. This should move to the server
    lib project eventually and use its own driver object (preferably involving
    moving the drivers themselves to the serverlib)
    """

    # ensure there is a reference to the port
    if not robot.is_connected():
        robot.connect()
    for module in robot.modules:
        module.disconnect()
    robot.modules = modules.discover_and_connect()
    res = ''
    for module in robot.modules:
        if module.device_info.get('serial') == serialnum:
            log.info("Module with serial {} found".format(serialnum))
            bootloader_port = await modules.enter_bootloader(module)
            if bootloader_port:
                module._port = bootloader_port
            # else assume old bootloader connection on existing module port
            log.info("Uploading file to port:{} using config file {}".format(
                module.port, config_file_path))
            log.info("Flashing firmware. This will take a few seconds")
            try:
                res = await asyncio.wait_for(modules.update_firmware(
                    module, fw_filename, config_file_path, loop), 15)
            except asyncio.TimeoutError:
                return {'result': 'AVRDUDE not responding'}
            break
    if not res:
        res = {'result': 'Module {} not found'.format(serialnum)}
    return res
