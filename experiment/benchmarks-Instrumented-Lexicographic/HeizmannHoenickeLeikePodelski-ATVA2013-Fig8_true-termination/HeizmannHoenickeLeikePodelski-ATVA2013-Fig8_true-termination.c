#include <stdio.h>

int main()
{
    int x, y;
    scanf("%d%d", &x, &y);
    printf("[Testing] <Interface V3.0TR> (Basic lexical method)\n");

    if (2 * y >= 1)
    {
        while (x >= 0)
        {
            printf("%d,%d\n", x, y);
            x = x - 2 * y + 1;
        }
    }
    return 0;
}
