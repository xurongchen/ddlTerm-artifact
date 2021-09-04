function {:existential true} b0(x:int, y:int, z:int, tx:int %FD%, TR1:int, TR2:int): bool;

procedure main()
{
  var x,y,z,tx %VD%, TR1, TR2: int;
  havoc x;
  havoc y;
  havoc z;
  havoc tx;

  assume(-1073741823<=tx && tx<=1073741823);
  assume(-1073741823<=z && z<=1073741823);
  assume(-1073741823<=x && x<=1073741823);
  assume(y<=1073741823);

  %BE%
TR1 := 0;
TR2 := 0;
  	
  while (x >= y && x <= tx + z)
  invariant b0(x,y,z,tx %IC%, TR1, TR2);
  {
    %BT%
TR1 := 0;
TR2 := 0;
    if (*)
    {
TR1 := 1;
      z := z - 1;
      tx := x;
      havoc x;
      assume(-1073741823<=x && x<=1073741823);
    }
    else
    {
TR2 := 1;
      y := y + 1;
    }
    %IT%
  }
}
