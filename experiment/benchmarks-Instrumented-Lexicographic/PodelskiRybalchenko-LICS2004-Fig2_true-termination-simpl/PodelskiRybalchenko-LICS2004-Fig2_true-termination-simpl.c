#include <stdio.h>
#include <stdlib.h>

int main()
{
    int x, y;
    scanf("%d%d", &x, &y);
    printf("[Testing] <Interface V3.0TR> (Basic lexical method)\n");

    while (x > 0 && y > 0)
    {
        printf("%d,%d\n", x, y);

        int old_x = x;
        int old_y = y;
        x = old_y - 2;
        y = old_x + 1;
    }
    return 0;
}
