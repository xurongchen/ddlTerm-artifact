function {:existential true} b0(x:int, i:int %Decl:i%): bool;

procedure main()
{
  var x,i: int;
  havoc x;

  assume(%M:i%);

  while (x > 0)
  invariant b0(x,i %Inv:i%);
  {
    assert(i > 0);
    x := -2*x + 10;
    i := i - 1;
  }
}
