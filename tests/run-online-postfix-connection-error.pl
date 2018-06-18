#!/usr/bin/perl -w
use IPC::Open2;
$| = 1; # Autoflush on
my $pid = open2(\*PROG, \*COMMAND, "./xcauth.py", "-t", "postfix", "-u", "https://no-connection.jsxc.org/", "-s", "0") or die "$!";
print COMMAND "get user\@example.org\n";
$data = <PROG>;
chomp $data;
if ($data !~ /^400 /) {
  print STDERR "**** Test for connection failure failed: $data\n";
  exit(1);
} else {
  print STDERR "**** Test for connection failure succeeded\n\n";
}
