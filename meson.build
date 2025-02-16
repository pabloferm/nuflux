project('nuflux', 'cpp',
        version : '2.0.0',
        default_options : ['cpp_std=c++11'])

cfitsio = dependency('cfitsio')
photospline = dependency('photospline', method : 'cmake')

datadir = get_option('data_path')
if datadir == ''
  datadir = get_option('prefix') / get_option('datadir') / meson.project_name()
endif
conf_data = configuration_data()
conf_data.set_quoted('DATA_DIR',datadir)
configure_file(output : 'config.h',
               configuration : conf_data)
if get_option('install_data')
  install_subdir('nuflux/data/',
                 install_dir:datadir,
                 strip_directory:true)
endif

subdir('src/include/nuflux')

inc = include_directories('src/include')
libnuflux = library(
  'nuflux',
  'src/library/ANFlux.cpp',
  'src/library/IPLEFlux.cpp',
  'src/library/LegacyConventionalFlux.cpp',
  'src/library/SplineFlux.cpp',
  'src/library/SplineFlux2.cpp',
  'src/library/FluxFunction.cpp',
  'src/library/LegacyPromptFlux.cpp',
  'src/library/logging.cpp',
  'src/library/detail.cpp',
  include_directories : inc,
  dependencies : [photospline,cfitsio],
  install : true)

test('test_basic',
     executable('test_basic',
                'tests/test_basic.cxx',
                dependencies : [photospline,cfitsio],
                include_directories : inc,
                link_with:libnuflux))

pkg_mod = import('pkgconfig')
pkg_mod.generate(
  libraries : libnuflux,
  version : meson.project_version(),
  name : meson.project_name(),
  filebase :  meson.project_name(),
  url : 'https://github.com/IceCubeOpenSource/nuflux',
  description : 'A library for calculating atmospheric neutrino fluxes')

cppcomp = meson.get_compiler('cpp')
pymod = import('python')
python = pymod.find_installation(get_option('python'),required: false)

if not python.found()
  warning('Can\'t find python: "'+get_option('python')+'", skipping python build')
else
  pydep = python.dependency()

  # Find numpy
  numpy = run_command(python,'-c','import numpy;print(numpy.get_include())')
  if numpy.returncode()==0
    pybind_inc = include_directories(numpy.stdout().strip())
    message ('Numpy found: '+ numpy.stdout().strip())
  else
    warning ('Numpy not found: building without arrays')
    pybind_inc = include_directories()
  endif

  python_name = 'python'+''.join(python.language_version().split('.'))
  boost = dependency('boost'      , modules : [python_name])

  if not boost.found()
    warning( 'Can\'t find boost python, Skipping python build')
  else
    py_install_dir = python.get_install_dir() / 'nuflux'
    message( 'Building package for python version ' +
             python.language_version() + ': ' + py_install_dir)

    python.install_sources('nuflux/__init__.py',
                           subdir: py_install_dir,
                           )

    python.extension_module(
      '_nuflux',
      ['src/pybindings/module.cxx'],
      include_directories : [inc,pybind_inc],
      dependencies : [photospline,pydep, boost],
      link_with : libnuflux,
      install_dir : py_install_dir,
      install:true)

    test('test_fluxes',find_program('tests/test_fluxes.py'))

  endif

endif
