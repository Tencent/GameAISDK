from distutils.core import setup, Extension  
  
MOD = 'tbus'
setup(name=MOD, ext_modules=[ 
        Extension(MOD,  extra_compile_args=[], sources=['tbus.c'], include_dirs=['../../libtbus/include/'], library_dirs=['/usr/local/lib'], libraries=['tbus'])]) 
