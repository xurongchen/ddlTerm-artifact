function {:existential true} b0(x:int, y:int, z:int, i:int %Decl:i%): bool;

procedure main()
{
  var x,y,z,i: int;
  havoc x;
  havoc y;
  havoc z;

  assume(%M:i%);

  while (x < y)
  invariant b0(x,y,z,i %Inv:i%);
  {
    assert(i > 0);
    if (z > x) {
      x := x + 1;
    } else {
      z := z + 1;
    }
    i := i - 1;
  }
}