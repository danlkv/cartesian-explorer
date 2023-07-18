Development
===========

1. Clone the repository and install in editable mode, using ``[dev]`` to install dev dependencies:

    .. code-block:: bash

        git clone <url>
        cd cartesian-explorer
        pip install -e '.[dev]'

2. If you are using vscode and want to contribute to the documentation,
   you might want to install an extension for ``.rst`` editing and preview.

3. Run tests with pytest:
    
    .. code-block:: bash

        pytest

4. To build docs, you need to install `pandoc <https://pandoc.org/installing.html>`_.
   If you don't have root access, install `pypandoc-binary` python package, then
   run the following in python REPL:

    .. code-block:: python
        
        import pypandoc
        pypandoc.download_pandoc()
        print(pypandoc.get_pandoc_path())

   verify that pandoc binary is in your ``$PATH``. When pandoc is installed, you can build docs:
    
    .. code-block:: bash

        cd docs && make html