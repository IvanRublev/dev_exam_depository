from src.web.schemas.student import StudentCreate
from tests.conftest import assert_validation_error


def test_pass_student_create(build_json_student):
    json = build_json_student()
    assert StudentCreate(**json)


def test_fail_student_create_given_no_email(build_json_student):
    json = build_json_student()
    del json["email"]
    assert_validation_error(lambda: StudentCreate(**json), "email", "Field required")


def test_fail_student_create_given_invalid_email(build_json_student):
    json = build_json_student({"email": "invalid_email"})
    assert_validation_error(lambda: StudentCreate(**json), "email", "not a valid email address")


def test_fail_student_create_given_no_nickname(build_json_student):
    json = build_json_student()
    del json["nickname"]
    assert_validation_error(lambda: StudentCreate(**json), "nickname", "Field required")


def test_fail_student_create_given_too_long_nickname(build_json_student):
    json = build_json_student({"nickname": "a" * 33})
    assert_validation_error(lambda: StudentCreate(**json), "nickname", "at most 12 characters")


def test_fail_student_create_given_non_alpha_nickname(build_json_student):
    json = build_json_student({"nickname": "n! kname_123"})
    assert_validation_error(lambda: StudentCreate(**json), "nickname", "only alphanumeric characters")


def test_fail_student_create_given_no_first_name(build_json_student):
    json = build_json_student()
    del json["first_name"]
    assert_validation_error(lambda: StudentCreate(**json), "first_name", "Field required")


def test_fail_student_create_given_too_long_first_name(build_json_student):
    json = build_json_student({"first_name": "a" * 255})
    assert_validation_error(lambda: StudentCreate(**json), "first_name", "at most 254 characters")


def test_fail_student_create_given_no_alpha_punctuation_first_name(build_json_student):
    json = build_json_student({"first_name": "n! kname_123"})
    assert_validation_error(lambda: StudentCreate(**json), "first_name", "only alpha characters and punctuation")


def test_fail_student_create_given_no_last_name(build_json_student):
    json = build_json_student()
    del json["last_name"]
    assert_validation_error(lambda: StudentCreate(**json), "last_name", "Field required")


def test_fail_student_create_given_too_long_last_name(build_json_student):
    json = build_json_student({"last_name": "a" * 255})
    assert_validation_error(lambda: StudentCreate(**json), "last_name", "at most 254 characters")


def test_fail_student_create_given_no_alpha_punctuation_last_name(build_json_student):
    json = build_json_student({"last_name": "name@#123"})
    assert_validation_error(lambda: StudentCreate(**json), "last_name", "only alpha characters and punctuation")
