#!/usr/bin/perl -w
use IPC::Open2;
if ( ! -r "/etc/xcauth.accounts" ) {
  print STDERR "/etc/xcauth.accounts must exist and be readable\n";
  exit(1);
}
$| = 1; # Autoflush on
open STDIN, "</etc/xcauth.accounts" or die;
my $child = -1;
my $pid = -1;
my $opt = shift;
if ($opt eq "socket1366x") {
  # Start our own service on ports 1366x
  $child = fork();
  if ($child < 0) {
    die "fork: $!";
  } elsif ($child == 0) {
    exec 'systemd-socket-activate', 
    	'-l', '13662', '--fdname', 'ejabberd',
    	'-l', '13663', '--fdname', 'prosody',
    	'-l', '13665', '--fdname', 'postfix',
    	'-l', '/tmp/saslauthd-mux', '--fdname', 'saslauthd',
       	'./xcauth.py', '-t', 'generic';
    die "exec: $!";
  } else {
    sleep(1);
    $pid = open2(\*PROG, \*COMMAND, "socket", "/tmp/saslauthd-mux") or die "$!";
  }
} elsif ($opt eq "socket2366x") {
  # Use active systemd services on ports 2366x
  $pid = open2(\*PROG, \*COMMAND, "socket", "/var/run/saslauthd/mux") or die "$!";
} else {
  # Use pipe to child process
  $pid = open2(\*PROG, \*COMMAND, "./xcauth.py", "-t", "saslauthd") or die "$!";
}
binmode(COMMAND);
binmode(PROG);
$u = '';
$d = '';
$p = '';
while (<>) {
  chomp;
  next if length($_) == 0 || substr($_, 0, 1) eq '#';
  @fields = split(/\t/, $_, -1);
  if ($#fields != 2) {
    print STDERR "Need 3 fields per line: $_\n";
    exit(1);
  }
  if ($fields[0] eq '') {
    if ($fields[1] eq 'auth') {
      $cmd = lstr($u) . lstr($p) . lstr('test') . lstr($d);
      print COMMAND $cmd;
    } elsif ($fields[1] eq 'isuser') {
      print STDERR "Not testing isuser command in saslauthd mode\n";
      next;
    } elsif ($fields[1] eq 'roster') {
      print STDERR "Not testing roster command in saslauthd mode\n";
      next;
    } else {
      print STDERR "Invalid command $fields[1]\n";
      exit(1);
    }
    sysread PROG, $len, 2;
    $len = unpack('n', $len);
    sysread PROG, $data, $len;
    # Normalization
    if ($data =~ /^NO /) {
      $data = "False";
    } elsif ($data =~ /^OK /) {
      $data = "True";
    }

    if ($data ne $fields[2]) {
      print STDERR "*** Test " . join(' ', @fields[1,2]) . " failed ($u/$d/$p: $data != $fields[2])\n";
      exit(1);
    } else {
      print STDERR "*** Test " . join(' ', @fields[1,2]) . " succeeded\n\n";
    }
  } else {
    ($u, $d, $p) = @fields;
  }
}
if ($child > 0) {
  kill('TERM', $child);
}
if ($pid > 0) {
  kill('TERM', $pid);
}

sub lstr {
  my $s = shift;
  return pack("n", length($s)) . $s;
}
