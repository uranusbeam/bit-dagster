import copy

from dagster import check


def _deep_merge_dicts(onto_dict, from_dict):
    check.dict_param(from_dict, 'from_dict')
    check.dict_param(onto_dict, 'onto_dict')

    for from_key, from_value in from_dict.items():
        if from_key not in onto_dict:
            onto_dict[from_key] = from_value
        else:
            onto_value = onto_dict[from_key]

            if isinstance(from_value, dict) and isinstance(onto_value, dict):
                onto_dict[from_key] = _deep_merge_dicts(from_value, onto_value)
            else:
                onto_dict[from_key] = from_value  # smash

    return onto_dict


def deep_merge_dicts(onto_dict, from_dict):
    '''
    Returns a recursive union of two input dictionaries:
    * The returned dictionary has an entry for any key that's in either of the inputs.
    * For any key whose value is a dictionary in both of the inputs, the returned value will
      be the result of deep-merging the two input sub-dictionaries.

    If from_dict and onto_dict have different values for the same key, and the values are not both
    dictionaries, the returned dictionary contains the value from from_dict.
    '''
    onto_dict = copy.deepcopy(onto_dict)
    return _deep_merge_dicts(onto_dict, from_dict)


def merge_dicts(onto_dict, from_dict):
    '''
    Returns a dictionary with an entry for any key that's in either of the inputs.
    If the inputs have different values for the same key, the returned dictionary
    contains the value from from_dict.
    '''
    check.dict_param(onto_dict, 'onto_dict')
    check.dict_param(from_dict, 'from_dict')

    result = onto_dict.copy()
    result.update(from_dict)
    return result
