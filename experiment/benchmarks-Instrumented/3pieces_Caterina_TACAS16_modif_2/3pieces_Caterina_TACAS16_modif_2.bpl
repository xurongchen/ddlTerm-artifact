function {:existential true} b0(x:int, y:int, i:int %Decl:i%): bool;

procedure main()
{
  var x,y,i: int;
  havoc x;
  havoc y;

  assume(%M:i%);
  	
  while (x != 0)
  invariant b0(x,y,i %Inv:i%);
  {
    assert(i > 0);
    y := y - 1;
    if(x < 10){
      x := x + 1;
    }
    else {
      x := y;
    }
    i := i - 1;
  }
}