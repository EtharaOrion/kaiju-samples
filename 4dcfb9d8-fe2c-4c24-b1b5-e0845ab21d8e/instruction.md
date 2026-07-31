# Implement `ramonhagenaars/jsons`

You are given a Python repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a `pass` statement.

You need to complete the implementations for all functions (i.e., those with `pass` statements) and pass the unit tests.
Do not change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `ramonhagenaars/jsons`
- Source directory to implement: `jsons/`
- Test command: `pytest` (run against `tests`)
- Specification / docs: 

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

API Main functions dump This is the main serialization function of jsons. It will look for the best fitting serializer function that is registered and use that to turn the given object to a JSON compatible type.

Any parameter of a serializer function, can be set using the keyword arguments of dump. Here is an overview of the standard options: Parameter Type Description strip_microseconds bool Microseconds are not included in serialized datetimes.

strip_nulls bool The resulting JSON will not contain attributes with values that are null.

strip_privates bool Private attributes (starting with _) are omitted.

strip_properties bool Properties (@property) are omitted.

use_enum_name bool When True, enums are serialized as their names. Otherwise their values are used.

key_transformer Callable[[str], str] Transforms the keys of the resulting dict. For example, jsons.KEY_TRANSFORMER_CAMELCASE turns all keys in ‘camelCase’.

verbose verbose: Union[Verbosity, bool] This parameter allows you to specify whether and how meta data should be outputted. If WITH_CLASS_INFO or WITH_EVERYTHING is used, the output contain typing info. With that info jsons.load does not need a cls argument.

Here is an example: >>> @dataclass ... class C: ... _foo: int ... bar: int >>> c = C(1, 2) >>> jsons.dump(c, strip_privates=True) {'bar': 2} For more info, check out the parameters of the serializers.

Function signature: Function: jsons.dump Description: Serialize the given object to a JSON compatible type (e.g. dict, list, string, etc.)

Arguments: obj: object The object that is to be serialized.

cls: Optional[type] If given, obj will be dumped as if it is of type type.

fork_inst: Optional[type] If given, the serializer functions of this fork of JsonSerializable are used.

kwargs Keyword arguments will be passed on to the serializer functions.

Returns: object The serialized obj as a JSON type.

latest Example: >>> some_utcdate = datetime.now(tz=timezone.utc) >>> jsons.dump(some_utcdate) '2019-02-16T20:33:36Z' load Function: jsons.load Description: Deserialize the given object to a Python equivalent type or an instance of type cls (if given).

Arguments: json_obj: object The object that is to be deserialized.

cls: Optional[type] A matching class of which an instance should be returned.

strict: bool Determines strict mode (e.g. fail on partly deserialized objects).

fork_inst: Optional[type] If given, the deserializer functions of this fork of JsonSerializable are used.

attr_getters: Optional[Dict[str, Callable[[], object]]] A dict that may hold callables that return values for certain attributes.

kwargs Keyword arguments will be passed on to the deserializer functions.

Returns: object An object of a Python equivalent type or of cls.

Example: >>> jsons.load('2019-02-16T20:33:36Z', datetime) datetime.datetime(2019, 2, 16, 20, 33, 36, tzinfo=datetime.timezone.utc) dumps Function: jsons.dumps Description: Serialize the given object to a string.

Arguments: obj: object The object that is to be stringified.

jdkwargs Extra keyword arguments for json.dumps (not jsons.dumps!)

args Extra arguments for jsons.dumps.

kwargs Keyword arguments that are passed on through the serialization process.

Returns: object An object of a Python equivalent type or of cls.

Example: >>> jsons.dumps([1, 2, 3]) '[1, 2, 3]' loads Function: jsons.loads Description: Deserialize a given JSON string to a Python equivalent type or an instance of type cls (if given).

Arguments: str_: str The string containing the JSON that is to be deserialized.

cls: Optional[type] A matching class of which an instance should be returned.

jdkwargs Extra keyword arguments for json.loads (not jsons.loads!).

args Extra arguments for jsons.load.

latest kwargs Keyword arguments that are passed on through the deserialization process.

Returns: object An object of a Python equivalent type or of cls.

Example: >>> jsons.loads('[1, 2, 3]') [1, 2, 3] dumpb Function: jsons.dumpb Description: Serialize the given object to bytes that contain JSON.

Arguments: obj: object The object that is to be serialized.

encoding: str The encoding that is used to transform from bytes.

jdkwargs Extra keyword arguments for json.dumps (not jsons.dumps!)

args Extra arguments for jsons.dumps.

kwargs Keyword arguments that are passed on through the serialization process.

Returns: bytes A serialized obj in bytes.

Example: >>> jsons.dumpb([1, 2, 3]) b'[1, 2, 3]' loadb Function: jsons.loadb Description: Deserialize the given bytes holding JSON to a Python equivalent type or an instance of type cls (if given).

Arguments: bytes_: bytes The bytes containing the JSON that is to be deserialized.

cls: Optional[type] A matching class of which an instance should be returned.

encoding: str The encoding that is used to transform from bytes.

jdkwargs Extra keyword arguments for json.loads (not jsons.loads!)

args Extra arguments for jsons.loads.

kwargs Keyword arguments that are passed on through the deserialization process.

Returns: object An object of a Python equivalent type or of cls.

Example: >>> jsons.loadb(b'[1, 2, 3]') [1, 2, 3] fork Function: jsons.fork Description: Create a “fork instance” that contains its own settings (serializers, deserializers, etc.) separately.

Arguments: fork_inst: Type[T] If given, the new fork is based on the given fork.

latest name: Optional[str] The name of the newly created fork.

Returns: Type[T] A “fork instance” that you can pass to most jsons functions (e.g. dump).

Example: >>> fork_inst = jsons.fork() >>> jsons.set_serializer(lambda *_, **__: 'Fork!', str, fork_inst=fork_inst) >>> jsons.dump('Any string') 'Any string' >>> jsons.dump('Any string', fork_inst=fork_inst) 'Fork!'

set_serializer Function: jsons.set_serializer Description: Set a serializer function for the given type. The callable must accept at least two arguments: the object to serialize and kwargs. It must return an object that has a JSON equivalent type (e.g. dict, list, string, …).

Arguments: func: callable The serializer function.

cls: Union[type, Sequence[type]] The type or sequence of types that func can serialize.

high_prio: bool If True, then func will take precedence over any other serializer function that serializes cls.

fork_inst If given, it registers func to this fork of JsonSerializable, rather than the global jsons.

Returns: None

Example: >>> jsons.set_serializer(lambda obj, **_: 123, str) >>> jsons.dump('any string') 123 get_serializer Function: jsons.get_serializer Description: Return the serializer function that would be used for the given cls.

Arguments: cls: type The type of which the deserializer is requested.

fork_inst If given, it uses this fork of JsonSerializable.

Returns: callable The serializer function.

Example: >>> jsons.get_serializer(str) <function get_serializer at 0x02F36A50> set_deserializer Function: jsons.set_deserializer Description: Set a deserializer function for the given type. The callable must accept at least three arguments: the object to deserialize, the type to deserialize to and kwargs. It must return a deserialized object of type cls.

Arguments: func: callable The deserializer function.

cls: Union[type, Sequence[type]] The type or sequence of types that func can deserialize.

latest high_prio: bool If True, then func will take precedence over any other deserializer function that serializes cls.

fork_inst If given, it registers func to this fork of JsonSerializable, rather than the global jsons.

Returns: None

Example: >>> jsons.set_deserializer(lambda obj, cls, **_: 123, str) >>> jsons.load('any string') 123 get_deserializer Function: jsons.get_deserializer Description: Return the deserializer function that would be used for the given cls.

Arguments: cls: type The type of which the deserializer is requested.

fork_inst If given, it uses this fork of JsonSerializable.

Returns: callable The deserializer function.

Example: >>> jsons.get_deserializer(str) <function get_deserializer at 0x02F36A98> suppress_warnings Function: jsons.set_deserializer Description: Suppress (or stop suppressing) warnings.

Arguments: do_suppress: Optional[bool] if True, warnings will be suppressed from now on.

cls: type The type that func can deserialize.

high_prio: bool If True, then func will take precedence over any other deserializer function that serializes cls.

fork_inst If given, it only suppresses (or stops suppressing) warnings of the given fork.

Returns: None

Example: >>> jsons.suppress_warnings() set_validator Function: jsons.set_validator Description: Set a validator function for the given cls. The function should accept an instance of the type it should validate and must return False or raise any exception in case of a validation failure.

Arguments: func: callable The function that takes an instance of type cls and returns a bool (True if the validation was successful).

cls: Union[type, Sequence[type]] The type or types that func is able to validate.

fork_inst If given, it registers func to this fork of JsonSerializable, rather than the global jsons.

latest Returns: None

Example: >>> jsons.set_validator(lambda x: x >= 0, int) >>> jsons.load(-1) jsons.exceptions.ValidationError: Validation failed.

get_validator Function: jsons.get_validator Description: Return the validator function that would be used for the given cls.

Arguments: cls: type The type of which the validator is requested.

fork_inst If given, it uses this fork of JsonSerializable.

Returns: callable The validator function.

Example: >>> jsons.get_validator(str) <function str_validator at 0x02F36A98> Classes JsonSerializable This class can be used as a base class for your models.

@dataclass class Car(JsonSerializable): color: str owner: str You can now dump your model using the json property: car = Car('red', 'Gary') dumped = car.json # == jsons.dump(car) The JSON data can now also be loaded using your model: loaded = Car.from_json(dumped) # == jsons.
