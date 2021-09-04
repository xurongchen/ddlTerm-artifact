function {:existential true} b0(x:int, y:int, z:int, i:int %Decl:i%): bool;

procedure main()
{
  var x,y,z,i: int;

  havoc x;
  havoc y;
  havoc z;

  assume(x > 1);
  assume(y > 1);
  assume(z > 1);
  assume(%M:i%);
  	
  while (x < 1000000)
  invariant b0(x,y,z,i %Inv:i%);
  {
    assert(i > 0);
    x := x * y * z;
    
    i := i - 1;
  }
}
