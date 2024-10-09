struct fizz;

void test() {}

int test_switch() {
  switch (0) {
  case 0:
    return 0;
    break;
  case 1:
    return 1;
    break;
  default:
    return 2;
    break;
  }
}

void test_while() {
  while (0) {
    return;
  }
}

int bar(int a) {
  goto label_test;
  if (a) {
  label_test:
    return 1;
  } else {
    return 2;
  }
}

int test_elseif() {
  if (1) {
    return 0;
  } else if (0) {
    return 1;
  } else {
    return 2;
  }
}

int test_varif() {
  int i = 1;
  if (i) {
    return 1;
  } else {
    return 2;
  }
}

int foo() {
  if (1) {
    return 1;
  } else {
  label_test2:
    return 2;
  }

  if (0)
    return 1;
}

int main() { return foo() + bar(1); }
