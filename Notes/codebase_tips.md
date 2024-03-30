# Codebase Tips

This codebase is a multi-generational. Here are some small tips to get started.

## Python

Let's discuss some weird Python semantics/syntax you'll see around here.

### Modules

Each file in `src` is a **module**. These are imported by typing `import module_name` in a file.

However, modules can also contain other modules. For example, the `libs` folder is technically a module, containing submodules like `Drive`, `Location`, etc.

To import a submodule that's in a folder, you'd usually type `from folder_name import submodule_name`. But! Some of the modules, like `examples`, aren't inside `src`.

That means you have to use the import dot syntax to use them.

- `.` represents the current directory (submodule).
- `..` represents the previous directory (module).

So, to get `src/libs/Location.py` from `examples/ar.py`, you'll have to:

- escape from the `examples` module with `..`
- enter the `src/libs` submodule with `src.libs`  
- import the `Location` module

From these steps, you'll end up with: `from ..src.libs import Location`. It looks a bit weird, but it's consistent and keeps example/test code from our actual libraries.
