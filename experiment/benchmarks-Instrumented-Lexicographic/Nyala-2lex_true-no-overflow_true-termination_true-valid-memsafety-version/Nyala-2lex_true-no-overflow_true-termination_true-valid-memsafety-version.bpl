function {:existential true} b0(x:int, y:int %FD%, TR1:int): bool;

procedure main()
{
  var x,y %VD%, TR1: int;
  havoc x;
  havoc y;

  %BE%
TR1 := 0;

  while (x > 0 && y > 0)
  invariant b0(x,y %IC%, TR1);
  {
	%BT%
TR1 := 0;
	y := y - x;
	if (y < 0) {
TR1 := 1;
		x := x - 1;
		havoc y;
	}
	%IT%
  }
}
