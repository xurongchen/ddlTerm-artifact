extern int __VERIFIER_nondet_int(void);

int main() {
  int i=0;
  int x=0;
  int y=0;
  int n=__VERIFIER_nondet_int();
  
  for(i=0; i<n; i++)
  {
    x = x-y;
    y = __VERIFIER_nondet_int();
    x = x+y;
  }
}
