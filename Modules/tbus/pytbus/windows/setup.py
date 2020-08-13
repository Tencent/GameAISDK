from distutils.core import setup, Extension

MOD = 'tbus'
setup(name=MOD, ext_modules=[
        Extension(MOD, sources=['tbus.c'], include_dirs=['../../tbusdll/busdll'], library_dirs=['./'], libraries=['busdll'])])
