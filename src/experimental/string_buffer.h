//
// Created by abdess on 4/5/18.
//

#ifndef NEW_ZPROXY_STREAM_BUFFER_H
#define NEW_ZPROXY_STREAM_BUFFER_H
#include <string>

class StringBuffer {
    public:
	StringBuffer();
	StringBuffer &operator<<(char const *s);
	StringBuffer &operator<<(int i);
	StringBuffer &operator<<(std::string const &s);
	StringBuffer &operator<<(StringBuffer const &s);
	std::string const &string() const;
	void erase(unsigned int end);
	void addData(char const *s, size_t size);

    private:
	std::string buffer;
};

#endif //NEW_ZPROXY_STREAM_BUFFER_H
