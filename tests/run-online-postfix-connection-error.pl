#!/usr/bin/perl -w
use IPC::Open2;
$| = 1; # Autoflush on
my $child = -1;
my $pid = -1;
my $opt = shift;
if ($opt eq "socket1366x" or $opt eq "socket2366x") {
  # Start our own service on a special port, because we need to fail
  $child = fork();
  if ($child < 0) {
    die "fork: $!";
  } elsif ($child == 0) {
    exec 'systemd-socket-activate', '-l', '12561', './xcauth.py', '-t', 'postfix', "-u", "https://no-connection.jsxc.org/", "-s", "0";
    die "exec: $!";
  } else {
    sleep(1);
    $pid = open2(\*PROG, \*COMMAND, "socket", "localhost", "12561") or die "$!";
  }
} else {
  # Use pipe to child process
  $pid = open2(\*PROG, \*COMMAND, "./xcauth.py", "-t", "postfix", "-u", "https://no-connection.jsxc.org/", "-s", "0") or die "$!";
}
print COMMAND "get user\@example.org\n";
$data = <PROG>;
chomp $data;
if ($data !~ /^400 /) {
  print STDERR "**** Test for connection failure failed: $data\n";
  exit(1);
} else {
  print STDERR "**** Test for connection failure succeeded\n\n";
}
if ($child > 0) {
  kill('TERM', $child);
}
if ($pid > 0) {
  kill('TERM', $pid);
}
