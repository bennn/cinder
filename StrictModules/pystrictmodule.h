// Copyright (c) Facebook, Inc. and its affiliates. (http://www.facebook.com)
#ifndef Py_STRICTM_H
#define Py_STRICTM_H

#include "Python.h"
#include "StrictModules/strict_module_checker_interface.h"

#ifndef Py_LIMITED_API
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
  PyObject_HEAD StrictModuleChecker* checker;
} StrictModuleLoaderObject;

typedef struct {
  PyObject_HEAD int valid_module;
  PyObject* module_name;
  PyObject* file_name;
  int module_kind;
  int stub_kind;
  PyObject* ast;
  PyObject* ast_preprocessed;
  PyObject* symtable;
  PyObject* errors;
} StrictModuleAnalysisResult;

PyAPI_DATA(PyTypeObject) StrictModuleLoader_Type;
PyAPI_DATA(PyTypeObject) StrictModuleAnalysisResult_Type;
PyAPI_DATA(const char*) MUTABLE_DEC;
PyAPI_DATA(const char*) LOOSE_SLOTS_DEC;
PyAPI_DATA(const char*) EXTRA_SLOTS_DEC;
PyAPI_DATA(const char*) ENABLE_SLOTS_DEC;
PyAPI_DATA(const char*) CACHED_PROP_DEC;

#define StrictModuleLoaderObject_Check(v) \
  (Py_TYPE(v) == &StrictModuleLoader_Type)

#ifdef __cplusplus
}
#endif
#endif /* Py_LIMITED_API */
#endif /* Py_STRICTM_H */
