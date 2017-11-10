#!/usr/bin/perl -w
if ( ! -r "/etc/xcauth.accounts" ) {
  print STDERR "/etc/xcauth.accounts must exist and be readable\n";
  exit(1);
}
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
      open PROG, "-|", "./xcauth.py", "-A", $u, $d, $p or die "$!";
    } elsif ($fields[1] eq 'isuser') {
      open PROG, "-|", "./xcauth.py", "-I", $u, $d or die "$!";
    } elsif ($fields[1] eq 'roster') {
      open PROG, "-|", "./xcauth.py", "-R", $u, $d or die "$!";
    } else {
      print STDERR "Invalid command $fields[1]\n";
      exit(1);
    }
    $data = <PROG>;
    # Normalization
    chomp $data;
    if ($data eq '[]' || $data eq '{"result":"success","data":{"sharedRoster":[]}}') {
      $data = 'None';
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
