// 
// ~16 x Faster than the ruby version.
// http://splicd.com/AAEJedBQk7s/19/43
//
#include <stdio.h>
#include <stdlib.h>

#include <fcntl.h>
#include <ctype.h>
#include <string.h>
#include <inttypes.h>

#include "art.h"

int main()
{
    art_tree t;
    init_art_tree(&t);
    int len;
    char buf[2493109];
    FILE *f = fopen("/usr/share/dict/words", "r");

    uintptr_t line = 1;
    while (fgets(buf, sizeof buf, f)) {
        len = strlen(buf);
        buf[len-1] = '\0';
        for (int n=0; n<len; n++)
            if ((int)buf[n] >= 65 && (int)buf[n] <= 90)
                goto infinite_loop;
        art_insert(&t, buf, len, (void*)line);
        line++;
infinite_loop:
        continue;
    }

    int len2;
    char buf2[1024];
    char *to = (char*)malloc(64);
    unsigned char* b = (unsigned char*)malloc(64);

    while (fgets(buf2, sizeof buf2, stdin))
    {
        int word_size = 0;
        int i;
        len2 = strlen(buf2);

        for (i=0; i<len2; i++) {
            if (buf2[i] != ' ' && buf2[i] != '\n') {
                word_size++;
            } else {
                if (word_size != 0) {
                    strncpy(to, &buf2[i-word_size], word_size);
                    to[word_size] = '\0';

                    //unsigned char* b = (unsigned char*)malloc(word_size+1);
                    memcpy(b, to, word_size+1);

                    // Naturally, http://www.youtube.com/watch?v=dQw4w9WgXcQ
                    for(char *p = to;*p;++p) *p=*p>0x40&&*p<0x5b?*p|0x60:*p;

                    uintptr_t val = (uintptr_t)art_search(&t, to, word_size+1);

                    if (val > 0) {
                        printf("%s", b);
                    } else {
                        printf("<%s>", b);
                    }
                    word_size = 0;
                }
                if (buf2[i] == '\n') printf("\n");
                if (buf2[i] == ' ') printf(" ");
            }
        }
    }

    return 0;
}
