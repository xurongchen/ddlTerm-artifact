extern int __VERIFIER_nondet_int(void);

int main()
{
  int x1=__VERIFIER_nondet_int();
  int x2=__VERIFIER_nondet_int();
  int x3=__VERIFIER_nondet_int();
  
  while(x1>0 && x2>0 && x3>0)
  {
    if (__VERIFIER_nondet_int() == 0) x1=x1-1;
    else if (__VERIFIER_nondet_int() == 0) x2=x2-1;
    else x3=x3-1;
  }

  return 0;
}

