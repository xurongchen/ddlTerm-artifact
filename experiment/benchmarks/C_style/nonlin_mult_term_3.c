extern int __VERIFIER_nondet_int(void);

int main()
{
  int x = __VERIFIER_nondet_int();
  int y = __VERIFIER_nondet_int();
  int z = __VERIFIER_nondet_int();
  
  if (x <= 1) return 0;
  if (y <= 1) return 0;
  if (z <= 1) return 0;
  
  while (x < 1000000)
  {
    x = x * y * z;
  }
}
