# Kutana

## Basic description

The main idea of kutana is several backends that have some common
functions (like receiving and replying to messages) combined into
one application that interacts with users in some way through different
plugins that use common backend functions or their special
options (for example, a direct call to the telegram method).

Each application should use a custom value configuration used
internally by the application or its plugins (e.g. `prefixes`),
a list of backend configurations (used to interact with some
platforms such as vk or tg), a storage list (used to store data
between launches or when not enough memory) and a list of
plugins (usually these are paths to folders with modules or
packages with plugins).

When loading plugins from a path, you should be aware that each
file is scanned, each package is iterated over, and only the plugin
instances stored in the `plugin` or `plugins` global variable will
be loaded into the application. You can see the loaded plugins
when you start the application.

Also, feel free to ask questions and offer notes for documents
in the github issues.

## Advanced usage

Most of the useful methods are documented in the sources. Therefore,
if you are interested in writing advanced applications, you should
refer to them. Interaction with users occurs mainly through methods
of the `Plugin` (setting up hooks and callbacks, e.t.c) and `Context`
(replying, performing requests, e.t.c) classes.
