from kutana.plugins.converters import vk, dumping

def get_convert_to_message(controller_type):
    if controller_type == "vk":
        return vk.convert_to_message

    elif controller_type == "dumping":
        return dumping.convert_to_message

    else:
        raise RuntimeError("No converter for controller type {}".format(
            controller_type
        ))
