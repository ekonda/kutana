from kutana.plugins.converters import vk, dumping


def get_converter(ctrl_type):
    if ctrl_type == "vk":
        return vk.convert_to_message

    elif ctrl_type == "dumping":
        return dumping.convert_to_message

    else:
        raise RuntimeError("No converter for controller type {}".format(
            ctrl_type
        ))
