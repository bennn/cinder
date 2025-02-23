#ifndef Py_CPYTHON_DICTOBJECT_H
#  error "this header file must not be included directly"
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _dictkeysobject PyDictKeysObject;

/* The ma_values pointer is NULL for a combined table
 * or points to an array of PyObject* for a split table
 */
typedef struct {
    PyObject_HEAD

    /* Number of items in the dictionary */
    Py_ssize_t ma_used;

    /* Dictionary version: globally unique, value change each time
       the dictionary is modified */
    uint64_t ma_version_tag;

    PyDictKeysObject *ma_keys;

    /* If ma_values is NULL, the table is "combined": keys and values
       are stored in ma_keys.

       If ma_values is not NULL, the table is splitted:
       keys are stored in ma_keys and values are stored in ma_values */
    PyObject **ma_values;
} PyDictObject;

PyAPI_FUNC(PyObject *) _PyDict_GetItem_KnownHash(PyObject *mp, PyObject *key,
                                       Py_hash_t hash);
PyAPI_FUNC(PyObject *) _PyDict_GetItemIdWithError(PyObject *dp,
                                                  struct _Py_Identifier *key);
PyAPI_FUNC(PyObject *) _PyDict_GetItemStringWithError(PyObject *, const char *);
PyAPI_FUNC(PyObject *) PyDict_SetDefault(
    PyObject *mp, PyObject *key, PyObject *defaultobj);
PyAPI_FUNC(int) _PyDict_SetItem_KnownHash(PyObject *mp, PyObject *key,
                                          PyObject *item, Py_hash_t hash);
PyAPI_FUNC(int) _PyDict_DelItem_KnownHash(PyObject *mp, PyObject *key,
                                          Py_hash_t hash);
PyAPI_FUNC(int) _PyDict_DelItemIf(PyObject *mp, PyObject *key,
                                  int (*predicate)(PyObject *value));
PyDictKeysObject *_PyDict_NewKeysForClass(void);
PyAPI_FUNC(PyObject *) PyObject_GenericGetDict(PyObject *, void *);
PyAPI_FUNC(int) _PyDict_Next(
    PyObject *mp, Py_ssize_t *pos, PyObject **key, PyObject **value, Py_hash_t *hash);

/* Get the number of items of a dictionary. */
#define PyDict_GET_SIZE(mp)  (assert(PyDict_Check(mp)),((PyDictObject *)mp)->ma_used)
PyAPI_FUNC(int) _PyDict_Contains(PyObject *mp, PyObject *key, Py_hash_t hash);
PyAPI_FUNC(PyObject *) _PyDict_NewPresized(Py_ssize_t minused);
PyAPI_FUNC(void) _PyDict_MaybeUntrack(PyObject *mp);
PyAPI_FUNC(int) _PyDict_HasOnlyStringKeys(PyObject *mp);
Py_ssize_t _PyDict_KeysSize(PyDictKeysObject *keys);
PyAPI_FUNC(Py_ssize_t) _PyDict_SizeOf(PyDictObject *);
PyAPI_FUNC(PyObject *) _PyDict_Pop(PyObject *, PyObject *, PyObject *);
PyObject *_PyDict_Pop_KnownHash(PyObject *, PyObject *, Py_hash_t, PyObject *);
PyObject *_PyDict_FromKeys(PyObject *, PyObject *, PyObject *);
#define _PyDict_HasSplitTable(d) ((d)->ma_values != NULL)
/* facebook begin t39538061 */
Py_ssize_t
_PyDictKeys_GetSplitIndex(PyDictKeysObject *keys, PyObject *key);
/* facebook end t39538061 */

PyAPI_FUNC(int) PyDict_ClearFreeList(void);

/* Like PyDict_Merge, but override can be 0, 1 or 2.  If override is 0,
   the first occurrence of a key wins, if override is 1, the last occurrence
   of a key wins, if override is 2, a KeyError with conflicting key as
   argument is raised.
*/
PyAPI_FUNC(int) _PyDict_MergeEx(PyObject *mp, PyObject *other, int override);
PyAPI_FUNC(PyObject *) _PyDict_GetItemId(PyObject *dp, struct _Py_Identifier *key);
PyAPI_FUNC(int) _PyDict_SetItemId(PyObject *dp, struct _Py_Identifier *key, PyObject *item);

PyAPI_FUNC(int) _PyDict_DelItemId(PyObject *mp, struct _Py_Identifier *key);
PyAPI_FUNC(void) _PyDict_DebugMallocStats(FILE *out);

int _PyObjectDict_SetItem(PyTypeObject *tp, PyObject **dictptr, PyObject *name, PyObject *value);
PyObject *_PyDict_LoadGlobal(PyDictObject *, PyDictObject *, PyObject *);

/* _PyDictView */

typedef struct {
    PyObject_HEAD
    PyDictObject *dv_dict;
} _PyDictViewObject;

PyAPI_FUNC(PyObject *) _PyDictView_New(PyObject *, PyTypeObject *);
PyAPI_FUNC(PyObject *) _PyDictView_Intersect(PyObject* self, PyObject *other);

PyObject *_PyDict_GetAttrItem_Unicode(PyObject *op, PyObject *key);
PyObject *_PyDict_GetItem_Unicode(PyObject *op, PyObject *key);
PyObject *_PyDict_GetItem_String_KnownHash(PyObject *op,
                                           const char *key,
                                           Py_ssize_t len,
                                           Py_hash_t hash);
PyObject *_PyDict_GetItem_UnicodeExact(PyObject *op, PyObject *key);
PyAPI_FUNC(PyObject *) _PyDict_GetItemIdWithError(PyObject *dp,
                                                  struct _Py_Identifier *key);
PyObject *_PyDict_GetItem_StackKnownHash(PyObject *op,
                                         PyObject *const *stack,
                                         Py_ssize_t nargs,
                                         Py_hash_t hash);
/* Return 1 if the given dict has unicode-only keys and can be watched, or 0
 * otherwise. */
int _PyDict_CanWatch(PyObject *);

/* Return 1 if the given dict is watched, or 0 otherwise. */
int _PyDict_IsWatched(PyObject *);

/* Watch the given dict for changes, calling
 * _PyJIT_NotifyDict{Key,Clear,Unwatch}() as appropriate for any
 * changes to it. */
void _PyDict_Watch(PyObject *);

/* Stop watching the given dict. */
void _PyDict_Unwatch(PyObject *);

/* Return 1 if the given dict has deferred objects, or 0 otherwise. */
int _PyDict_HasDeferredObjects(PyObject *);

/* Flag dictionary as having deferred objects in it */
void _PyDict_SetHasDeferredObjects(PyObject *);

/* Unflag dictionary as having deferred objects in it */
void _PyDict_UnsetHasDeferredObjects(PyObject *);

int _PyDict_LoadDeferred(PyDictObject *);

/* Increment the given dict's version tag for a set operation, notifying any
 * watchers of the new value.
 */
void
_PyDict_IncVersionForSet(PyDictObject *dp, PyObject *key, PyObject *value);

PyAPI_FUNC(PyObject *) _PyDict_GetItemMissing(PyObject *mp, PyObject *key);

PyObject *_PyCheckedDict_New(PyTypeObject *type);
PyObject *_PyCheckedDict_NewPresized(PyTypeObject *type, Py_ssize_t minused);

int _PyDict_SetItem(PyObject *op, PyObject *key, PyObject *value);

int _PyCheckedDict_Check(PyObject *x);

/* Force the dictionary to use a combined layout.
 * Returns 0 on success or -1 on error.
 */
int _PyDict_ForceCombined(PyObject *);

#ifdef __cplusplus
}
#endif
