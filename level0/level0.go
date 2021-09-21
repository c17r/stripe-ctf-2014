package main

import ("os"
		"io/ioutil"
 		"fmt"
 		"bufio"
 		"regexp"
 		"strings")

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func getReaderContents(filename string) string {
	file, err := os.Open(filename)
	check(err)
	defer file.Close()

	stat, err := file.Stat()
	check(err)

	bs := make([]byte, stat.Size())
	_, err = file.Read(bs)
	check(err)

	return string(bs)
}

func getNeedles() string {
	bytes, err := ioutil.ReadAll(os.Stdin)
	check(err)
	return string(bytes)
}

func makeHaystack(filename string) map[string]int {

	haystack := make(map[string]int)

	file, err := os.Open(filename)
	check(err)
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		hay := scanner.Text()
		haystack[hay] = 1
	}

	return haystack
}

func main() {
	filename := "/usr/share/dict/words"
	if len(os.Args) > 1 {
		filename = os.Args[1]
	}

	haystack := makeHaystack(filename)

	r := regexp.MustCompile("([^ \n]+)")

	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		line := scanner.Text()

		output := r.ReplaceAllStringFunc(line, func(m string) string {
				_, prs := haystack[strings.ToLower(m)]
				if prs {
					return m
				} else {
					return "<" + m + ">"
				}
			})

			fmt.Println(output)
	}
}
