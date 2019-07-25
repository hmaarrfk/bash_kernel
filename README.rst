A Jupyter kernel for Vivado

Heavily inspired from the Bash Kernel for Jupyter.

This requires IPython 3.

To install::

    # pip install -----
    git clone https://github.com/hmaarrfk/bash_kernel.git
    python vivavdo_kernel/install

To use it, run one of:

.. code:: shell

    jupyter notebook
    # In the notebook interface, select Bash from the 'New' menu
    jupyter qtconsole --kernel vivado
    jupyter console --kernel vivado

For details of how this works, see the Jupyter docs on `wrapper kernels
<http://jupyter-client.readthedocs.org/en/latest/wrapperkernels.html>`_, and
Pexpect's docs on the `replwrap module
<http://pexpect.readthedocs.org/en/latest/api/replwrap.html>`_
