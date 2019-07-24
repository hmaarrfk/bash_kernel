from ipykernel.kernelapp import IPKernelApp
from .kernel import VivadoKernel
IPKernelApp.launch_instance(kernel_class=VivadoKernel)
