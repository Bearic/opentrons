// @flow
import startCase from 'lodash/startCase'

import type {
  StepType,
  StepIdType,
  BlankForm
} from '../../form-types'

import {
  DEFAULT_CHANGE_TIP_OPTION,
  DEFAULT_WELL_ORDER_FIRST_OPTION,
  DEFAULT_WELL_ORDER_SECOND_OPTION,
  FIXED_TRASH_ID
} from '../../constants'

// TODO: type pipette
const generateNewForm = (stepId: StepIdType, stepType: StepType): BlankForm => {
  // Add default values to a new step form
  const baseForm = {
    id: stepId,
    stepType: stepType,
    'step-name': startCase(stepType),
    'step-details': ''
  }
  switch (stepType) {
    case 'transfer':
      return {
        ...baseForm,
        'aspirate_changeTip': DEFAULT_CHANGE_TIP_OPTION,
        'aspirate_wellOrder_first': DEFAULT_WELL_ORDER_FIRST_OPTION,
        'aspirate_wellOrder_second': DEFAULT_WELL_ORDER_SECOND_OPTION,
        'dispense_wellOrder_first': DEFAULT_WELL_ORDER_FIRST_OPTION,
        'dispense_wellOrder_second': DEFAULT_WELL_ORDER_SECOND_OPTION
      }
    case 'consolidate':
    case 'mix':
      return {
        ...baseForm,
        'aspirate_changeTip': DEFAULT_CHANGE_TIP_OPTION,
        'aspirate_wellOrder_first': DEFAULT_WELL_ORDER_FIRST_OPTION,
        'aspirate_wellOrder_second': DEFAULT_WELL_ORDER_SECOND_OPTION
      }
    case 'distribute':
      return {
        ...baseForm,
        'aspirate_changeTip': DEFAULT_CHANGE_TIP_OPTION,
        'aspirate_disposalVol_checkbox': true,
        'dispense_wellOrder_first': DEFAULT_WELL_ORDER_FIRST_OPTION,
        'dispense_wellOrder_second': DEFAULT_WELL_ORDER_SECOND_OPTION,
        'dispense_blowout_checkbox': true,
        'dispense_blowout_labware': FIXED_TRASH_ID
      }
    default:
      if (stepType !== 'pause') {
        console.warn('generateNewForm: Only transfer, consolidate, & pause forms are supported now. TODO. Got ' + stepType)
      }
      return baseForm
  }
}

export default generateNewForm
