//This file parses inputs from a file and turns them into assembly commands

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define LEX_SIZE 500 
#define MAX_STRING_LENGTH 20 
char lex[LEX_SIZE]; //stores input
char tokenList[LEX_SIZE][MAX_STRING_LENGTH]; //stores tokens to be printed at end
char identifiers[LEX_SIZE][MAX_STRING_LENGTH]; //gets all identifiers to easily check
int identIndex = 0;
enum TokenType 
{
    modsym = 1, identsym, numbersym, plussym, minussym,
    multsym, slashsym, fisym, eqlsym, neqsym,
    lessym, leqsym, gtrsym, geqsym, lparentsym,
    rparentsym, commasym, semicolonsym, periodsym, becomessym,
    beginsym, endsym, ifsym, thensym, whilesym,
    dosym, callsymNon, constsym, varsym, procsymNon,
    writesym, readsym, elsesym
};

typedef struct
{
    int kind; //constant 1, variable 2, procedure 3
    char name[MAX_STRING_LENGTH + 1]; 
    int val;
    int level;
    int address;
    int mark;
} symTable;

typedef struct 
{
    int op;
    int l;
    int m;
} InstReg;

int multCommentEnd(int j);
int endCheck(int i);
int varFind(char *str);


symTable symbol_table[LEX_SIZE]; //just set to lex size since 500 seems fine
InstReg code[LEX_SIZE]; 
int symCounter = 0;
int codeCounter = 0; 


int main(int argc, char* argv[])
{
    //ILE *fptr = fopen(argv[1], "rb"); 
    FILE *fptr = fopen("C:\\Users\\linco\\Coding\\Spring 25 Coding\\Sys Soft\\input2.txt", "rb");  
    FILE *fOut = fopen("parserOutput.txt", "w");

    if (fptr == NULL) //error detection if file pointer doesnt initialize properly
    {
       printf("Error! opening file");
       exit(1);
    }

    int tokenIndex = 0; //tracks and updates token array
    int ch; //integer because ASCII values for characters.
    int i = 0; //i declared here to work in while statement
    
    while ((ch = fgetc(fptr)) != EOF && i < LEX_SIZE - 1) //read characters one by one
    {
        lex[i] = ch; // store character into the lex array
        i++;
    }

    lex[i] = '\0'; //adds null terminator to end of input

    fclose(fptr); //closes file after reading

    printf("Input\n"); //prints input in entirety
    for(int i = 0; i < strlen(lex); i++)
    {
        printf("%c", lex[i]); 
    }

    tokenIndex = 0; //index for token array
    printf("\n\nLexeme Table:\n\n"); //sets up next phase and prints tokenable input
    printf("Lexeme\ttoken type\n");

    for(int j = 0; j < LEX_SIZE; j++) //massive if else statement that handles the input character by character, case by case
    {
        if(lex[j] == 'b' && lex[j + 1] == 'e' && lex[j + 2] == 'g' && lex[j + 3] == 'i' && lex[j + 4] == 'n') //these are out of order because i added them to complete my test case first and then moved to other cases
        {
            printf("begin\t\t21\n");
            j += 4;
            strcpy(tokenList[tokenIndex++], "21");
        }
        else if(lex[j] == 'e' && lex[j + 1] == 'n' && lex[j + 2] == 'd')
        {
            printf("end\t\t22\n");
            j += 2;
            strcpy(tokenList[tokenIndex++], "22");
        }
        else if(lex[j] == 'i' && lex[j + 1] == 'f')
        {
            printf("if\t\t23\n");
            j += 1;
            strcpy(tokenList[tokenIndex++], "23");
        }
        else if(lex[j] == 't' && lex[j + 1] == 'h' && lex[j + 2] == 'e' && lex[j + 3] == 'n' )
        {
            printf("then\t\t24\n");
            j += 3;
            strcpy(tokenList[tokenIndex++], "24");
        }
        else if(lex[j] == 'w' && lex[j + 1] == 'h' && lex[j + 2] == 'i' && lex[j + 3] == 'l' && lex[j + 4] == 'e')
        {
            printf("while\t\t25\n");
            j += 4;
            strcpy(tokenList[tokenIndex++], "25");
        }
        else if(lex[j] == 'd' && lex[j + 1] == 'o')
        {
            printf("do\t\t26\n");
            j += 1;
            strcpy(tokenList[tokenIndex++], "26");
        }
        else if(lex[j] == 'c' && lex[j + 1] == 'a' && lex[j + 2] == 'l' && lex[j + 3] == 'l' )
        {
            printf("call\t\t27\n");
            j += 3;
            strcpy(tokenList[tokenIndex++], "27");
        }
        else if(lex[j] == 'c' && lex[j + 1] == 'o' && lex[j + 2] == 'n' && lex[j + 3] == 's' && lex[j + 4] == 't')
        {
            printf("const\t\t28\n");
            j += 4;
            strcpy(tokenList[tokenIndex++], "28");
        }
        else if(lex[j] == 'v' && lex[j + 1] == 'a' && lex[j + 2] == 'r')
        {
            printf("var\t\t29\n");
            j += 2;
            strcpy(tokenList[tokenIndex++], "29");
        }
        else if(lex[j] == 'm' && lex[j + 1] == 'o' && lex[j + 2] == 'd')
        {
            printf("mod\t\t1\n");
            j += 2;
            strcpy(tokenList[tokenIndex++], "1");
        }
        else if ((lex[j] >= 'A' && lex[j] <= 'Z') || (lex[j] >= 'a' && lex[j] <= 'z')) //lex code for identifiers that are not keywords
        {
            char tempString[MAX_STRING_LENGTH];
            tempString[0] = lex[j];
            tempString[1] = '\0'; 
            int letCounter = 0; //keeps track of string size and sees if its valid during output
            while (isalpha(lex[j + 1])) //adds all detected letters to build string until end conditions are met
            {
                strcat(tempString, (char[]){lex[j + 1], '\0'}); //adds string to array
                j++;
                letCounter++;
            }

            if(letCounter < 11)
            {
                printf("%s\t\t2\n", tempString);
                strcpy(tokenList[tokenIndex++], "2"); //stores token number of Ident
                strcpy(tokenList[tokenIndex++], tempString); //stores ident
            }
            else
            {
                printf("%s\t\tError: Ident length too long\n", tempString);
                fprintf(fOut, "Error: Ident length too long");
                exit(0);
            }
        }
        else if(lex[j] == ',')
        {
            printf(",\t\t17\n");
            strcpy(tokenList[tokenIndex++], "17");
        }
        else if(lex[j] == '-')
        {
            printf("-\t\t34\n");
            strcpy(tokenList[tokenIndex++], "34");
        }
        else if(lex[j] == ';')
        {
            printf(";\t\t18\n");
            strcpy(tokenList[tokenIndex++], "18");
        }
        else if(lex[j] == ':' && lex[j + 1] == '=')
        {
            printf(":=\t\t20\n");
            strcpy(tokenList[tokenIndex++], "20");
            j += 1;
        }
        else if(lex[j] == '!' && lex[j + 1] == '=')
        {
            printf("!=\t\t10\n");
            strcpy(tokenList[tokenIndex++], "10");
            j += 1;
        }
        else if(lex[j] == '=')
        {
            printf("=\t\t22\n");
            strcpy(tokenList[tokenIndex++], "22");
        }
        else if(lex[j] == '*')
        {
            printf("*\t\t6\n");
            strcpy(tokenList[tokenIndex++], "6");
        }
        else if(lex[j] == '(')
        {
            printf("(\t\t15\n");
            strcpy(tokenList[tokenIndex++], "15");
        }
        else if(lex[j] == ')')
        {
            printf(")\t\t16\n");
            strcpy(tokenList[tokenIndex++], "16");
        }
        else if(lex[j] == '+')
        {
            printf("+\t\t4\n");
            strcpy(tokenList[tokenIndex++], "4");
        }
        else if(lex[j] == '-')
        {
            printf("-\t\t5\n");
            strcpy(tokenList[tokenIndex++], "5");
        }
        else if(lex[j] == ':')
        {
            printf("-\t\t20\n");
            strcpy(tokenList[tokenIndex++], "20");
        }
        else if(lex[j] == '.')
        {
            printf(".\t\t19\n");
            strcpy(tokenList[tokenIndex++], "19");
        }
        else if(isdigit(lex[j])) //covers numbers and sees if they are too large
        {
            int num = lex[j] - '0'; 
            int numCounter = 0;
            while((isdigit(lex[j+1]))) //so until there is a whitespace character it adds numbers
            {
                //it does this by multiplying current number by 10 and then adding the new number
                num = (num * 10) + (lex[j + 1] - '0');
                numCounter ++; 
                j++;        
            }
            
            if(numCounter < 5)
            {
                printf("%d\t\t3\n", num);
                strcpy(tokenList[tokenIndex++], "3"); //stores token index before actual number
                char numStr[MAX_STRING_LENGTH];
                sprintf(numStr, "%d", num); //converts number to string
                strcpy(tokenList[tokenIndex++], numStr);
            }
            else
            {
                printf("%d\t\tError: Number too long\n", num);
                fprintf(fOut, "Error: Number length too long");
                exit(0);
            }
        }
        else if(lex[j] == '/' && lex[j + 1] == '*') //multi line comment gets ignored
        {
            j = multCommentEnd(j); //no print statement since this just checks if a comment gets ended, and moves j appropiately
        }
        else if(lex[j] == '/') //single line comment gets tokenized
        {
            printf("/\t\t7\n");
            strcpy(tokenList[tokenIndex++], "7");
        }
        else if(lex[j] == '$')
        {
            printf("$\t\t12\n");
            strcpy(tokenList[tokenIndex++], "12");
        }
        else if(lex[j] == '%')
        {
            printf("%%\t\t14\n"); //double percent so it prints
            strcpy(tokenList[tokenIndex++], "14");
        }
        else if(lex[j] == '<' && lex[j + 1] == '>') //neqsym
        {
            printf("<>\t\t10\n");
            j += 2;
            strcpy(tokenList[tokenIndex++], "10");
        }
        else if(lex[j] == '<') //less than
        {
            printf("<\t\t11\n");
            strcpy(tokenList[tokenIndex++], "11");
        }
        else if(lex[j] == '>') //greater than
        {
            printf(">\t\t13\n");
            strcpy(tokenList[tokenIndex++], "13");
        
        }
        else if(lex[j] == '*') 
        {
            printf("*\t\t6\n");
            strcpy(tokenList[tokenIndex++], "6");
        }
        else if ((lex[j] >= 35 && lex[j] <= 126)) //base case for unrecognized symbols in the ASCII table
        {
            printf("%c\t\tError: Invalid symbol\n", lex[j]);
            fprintf(fOut, "Error: Invalid symbol");
            exit(0);
        }
    }

    printf("\nToken List\n\n");

    for(int i = 0; i < tokenIndex; i++)
    {
        printf("%s ", tokenList[i]);
    }

    printf("\n"); //newline just to make eustis output end on new line

    /*
    This begins the new section for HW3
    */

    for(int i = 0; i < tokenIndex; i++)
    {
        if((strcmp(tokenList[i], "2") == 0) && isalpha(tokenList[i + 1][0]))
        {
            strcpy(identifiers[identIndex], tokenList[i + 1]);
            identIndex++;
        }
    }

    printf("Assembly Code:\n");
    printf("JMP\t0\t13");
    if (endCheck(tokenIndex) == 1) //see if input has valid ending
    {
        printf("Error: Program must end with period\n");
        fprintf(fOut, "Error: Program must end with period");
        exit(0);
    }

    tokenIndex = 0;
    char token[MAX_STRING_LENGTH];//gets current token
    strcpy(token, tokenList[tokenIndex]);

    int level = 0;
    for (int i = 0; i < LEX_SIZE; i++)
    {
        code[i].op = 0;
        code[i].l = 0;
        code[i].m = 0;
    }

    return 0;
}

int multCommentEnd(int j) //checks to see if a comment has an end
{
    int endIndex = j; //return value
    for(int i = j; i < LEX_SIZE;i++) //iterates through lex starting from j to see if the comment ends
    {
        if(lex[i] == '*' && lex[i + 1] == '/') //comment ends, not tokenized
        {
            endIndex = i; //returns new spot in array since it skips comment
            return endIndex;
        }
    }

    return j; //comment doesnt have ending, returns J 
}

int endCheck(int i) //see if input has valid ending
{
    if (strcmp(tokenList[i - 1], "19") != 0) 
    {
        return 1;
    }
    else return 0;
}

int varFind(char *str) //takes in a string and see if it exists in the identifier array
{
    for(int i = 0; i < identIndex; i++)  //returns 1 if found, 0 or not
    {
        if (strcmp(identifiers[i], str) == 0) 
        {
            return 1;
        }
    }
    return 0; 
}