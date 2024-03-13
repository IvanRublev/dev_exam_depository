import re


def test_pass_student_has_upload_key_generated(build_models_student):
    student = build_models_student()
    assert re.match(r"^[A-Z0-9]{8}$", student.upload_code)
