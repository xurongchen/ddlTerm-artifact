function {:existential true} b0(id:int, maxId:int, tmp:int %FD%, TR1:int, TR2:int, ATTM$i$ADD$tmp:int): bool;

procedure main()
{
  var id, maxId, tmp %VD%, TR1, TR2: int;
  havoc id;
  havoc maxId;

  assume(0 <= id && id < maxId);
  tmp := id + 1;
  %BE%
TR1 := 0;
TR2 := 0;

  while (tmp != id)
  invariant b0(id, maxId, tmp %IC%, TR1, TR2, i + tmp);
  {
    %BT%
TR1 := 0;
TR2 := 0;
    if (tmp <= maxId)
    {
TR1 := 1;
        tmp := tmp + 1;
    }
    else
    {
TR2 := 1;
        tmp := 0;
    }
    %IT%
  }
}
