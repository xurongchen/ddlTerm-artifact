function {:existential true} b0(x:int, y:int, i:int %Decl:i%): bool;

procedure main()
{
  var x,y,i: int;

  havoc x;
  havoc y;

  assume(x > y);
  assume(%M:i%);
  	
  while (x != y)
  invariant b0(x,y,i %Inv:i%);
  {
    assert(i > 0);
    x := x - 2;
    y := y - 1;

    i := i - 1;
  }
}
