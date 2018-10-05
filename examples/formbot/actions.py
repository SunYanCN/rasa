# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import typing
from typing import Dict, Text, Any, List, Union

from rasa_core_sdk import ActionExecutionRejection
from rasa_core_sdk.forms import FormAction, REQUESTED_SLOT
from rasa_core_sdk.events import SlotSet

if typing.TYPE_CHECKING:
    from rasa_core_sdk import Tracker
    from rasa_core_sdk.executor import CollectingDispatcher


class RestaurantForm(FormAction):
    """Example of a custom form action"""

    def name(self):
        # type: () -> Text
        """Unique identifier of the form"""

        return "restaurant_form"

    @staticmethod
    def required_slots():
        # type: () -> List[Text]
        """A list of required slots that the form has to fill"""

        return ["cuisine", "num_people", "outdoor_seating",
                "preferences", "feedback"]

    def slot_mapping(self):
        # type: () -> Dict[Text: Union[Text, Dict, List[Text, Dict]]]
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of all of them, where a first match will be picked"""

        return {"cuisine": self.from_entity(entity="cuisine"),
                "num_people": [self.from_entity(entity="number"),
                               self.from_intent(intent='deny',
                                                value="number of people "
                                                      "not known")],
                "outdoor_seating": [self.from_entity(entity="seating"),
                                    self.from_intent(intent='affirm',
                                                     value=True),
                                    self.from_intent(intent='deny',
                                                     value=False)],
                "preferences": [self.from_text(intent='inform'),
                                self.from_intent(intent='deny',
                                                 value="no additional "
                                                       "preferences")],
                "feedback": [self.from_entity(entity="feedback"),
                             self.from_text()]}

    @staticmethod
    def cuisine_db():
        # type: () -> List[Text]
        """Database of supported cuisines"""
        return ["caribbean",
                "chinese",
                "french",
                "greek",
                "indian",
                "italian",
                "mexican"]

    @staticmethod
    def is_int(string):
        # type: (Text) -> bool
        """Check if a string is an integer"""
        try:
            int(string)
            return True
        except ValueError:
            return False

    def validate(self, dispatcher, tracker, domain):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict]
        """"Validate extracted requested slot else raise an error"""
        slot_to_fill = tracker.get_slot(REQUESTED_SLOT)

        # extract requested slot from a user input by using `slot_mapping`
        events = self.extract(dispatcher, tracker, domain)
        if events is None:
            # raise an error if nothing was extracted
            raise ActionExecutionRejection(self.name(),
                                           "Failed to validate slot {0} "
                                           "with action {1}"
                                           "".format(slot_to_fill,
                                                     self.name()))

        extracted_slots = []
        validated_events = []
        for e in events:
            if e['event'] == 'slot':
                # get values of extracted slots to validate them later
                extracted_slots.append(e['value'])
            else:
                # add other events without validating them
                validated_events.append(e)

        for slot in extracted_slots:
            if slot_to_fill == 'cuisine':
                if slot.lower() not in self.cuisine_db():
                    dispatcher.utter_template('utter_wrong_cuisine', tracker)
                    # validation failed, set this slot to None
                    validated_events.append(SlotSet(slot_to_fill, None))
                else:
                    # validation succeeded
                    validated_events.append(SlotSet(slot_to_fill, slot))

            elif slot_to_fill == 'num_people':
                if not self.is_int(slot) or int(slot) <= 0:
                    dispatcher.utter_template('utter_wrong_num_people',
                                              tracker)
                    # validation failed, set this slot to None
                    validated_events.append(SlotSet(slot_to_fill, None))
                else:
                    # validation succeeded
                    validated_events.append(SlotSet(slot_to_fill, slot))

            elif slot_to_fill == 'outdoor_seating':
                if isinstance(slot, bool):
                    # slot already boolean
                    validated_events.append(SlotSet(slot_to_fill, slot))
                elif 'out' in slot:
                    # convert out... to True
                    validated_events.append(SlotSet(slot_to_fill, True))
                elif 'in' in slot:
                    # convert in... to False
                    validated_events.append(SlotSet(slot_to_fill, False))
                else:
                    # set a slot to whatever it is
                    validated_events.append(SlotSet(slot_to_fill, slot))

            else:
                # no validation needed
                validated_events.append(SlotSet(slot_to_fill, slot))

        return validated_events

    def submit(self, dispatcher, tracker, domain):
        # type: (CollectingDispatcher, Tracker, Dict[Text, Any]) -> List[Dict]
        """Define what the form has to do
            after all required slots are filled"""

        # utter submit template
        dispatcher.utter_template('utter_submit', tracker)
        return []
