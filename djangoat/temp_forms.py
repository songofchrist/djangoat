"""
Create model field AutocompleteField that inherits from ChoiceField. When AutocompleteField is registered to a model
this will display on all admins as an autocomplete field and will behave according to the options set for the field
on the model. This should only be used when the autocomplete is to be universal.

Create form field AutocompleteField that can be used to make an autocomplete on any form for a field with choices.
Use MPTT as a model for how to do this:
https://github.com/django-mptt/django-mptt/blob/main/mptt/forms.py
https://github.com/django-mptt/django-mptt/blob/main/mptt/fields.py

Build this form field so that it works everywhere, both on sites and in the admin. Build it for sites first, then
incorporate it into the admin.

Need two versions. AutocompleteField for single choice and AutocompleteMultipleField for multiple choice. These
should be built of Django's native Select and SelectMultiple form inputs.

If a field is not registered on a model as autocomplete or needs settings overridden in the admin, do so via a
dg_autocomplete = {}, available via DgAdmin. This should take on of the following formats:
dg_autocomplete = {
    FIELD_1: RESULT_KEY_1  (associates this field with a key, used to return results)
    FIELD_2: {'key': RESULT_KEY_2}  (same as above)
    FIELD_3: {
        'key': RESULT_KEY_2,
        'forwards': {
            // uses jQuery selectors to grab data on the page prior to post, so values can be factored into response
            // if selector is for an input, captures value; if for an element, capture contents
            KEY_1: SELECTOR_1,
            KEY_2: SELECTOR_2
        },
        // executes function and captures output passing {FUNCTION_NAME_1: VALUE_1, FUNCTION_NAME_2: VALUE_2}
        'functions': [FUNCTION_NAME_1, FUNCTION_NAME_2, ...]
    }
}
"""