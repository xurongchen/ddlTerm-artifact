function {:existential true} b0(x:int, y:int, z:int, tx:int, i:int %Decl:i%): bool;

procedure main()
{
  var x,y,z,tx,i: int;
  havoc x;
  havoc y;
  havoc z;
  havoc tx;

  assume(%M:i%);
  	
  while (x >= y && x <= tx + z)
  invariant b0(x,y,z,tx,i %Inv:i%);
  {
    assert(i > 0);
    if (*)
    {
      z := z - 1;
      tx := x;
      havoc x;
    }
    else
    {
      y := y + 1;
    }
    i := i - 1;
  }
}
