extern int __VERIFIER_nondet_int(void);

int main()
{
  int x = __VERIFIER_nondet_int();
  int y = __VERIFIER_nondet_int();
  
  if (x <= 0) return 0;
  if (y <= 0) return 0;
  x = x*y;
  
  while (x != 0)
  {
    x = x - y;
  }
}
