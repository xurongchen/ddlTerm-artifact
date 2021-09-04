function {:existential true} b0(x:int, y:int, d:int, i:int %Decl:i%): bool;

procedure main()
{
  var x,y,d,i: int;
  havoc x;
  havoc y;
  havoc d;

  assume(%M:i%);

  while (x > 0 && y > 0 && d > 0)
  invariant b0(x,y,d,i %Inv:i%);
  {
    assert(i > 0);
    if (*) {
      x := x - 1;
      havoc d;
    } else {
      havoc x;
      y := y - 1;
      d := d - 1;
    }
    i := i - 1;
  }
}