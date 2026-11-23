%global debug_package %{nil}
Summary:	Glasgow Haskell Compiler 9.14.1 (bootstrapped with in-chain GHC 9.12.4)
Name:		ghc914
Version:	9.14.1
Release:	1
License:	BSD
Group:		Development/Other
Url:		https://www.haskell.org/ghc/
# Complement package. Does not replace distro ghc, so no Epoch.
# The host is packaged ghc912 (GHC 9.12.4). Hadrian dependencies,
# happy, and alex are in the bootstrap kit. This spec compiles the
# 9.14.1 sources; it does not copy a prebuilt prefix.
ExclusiveArch:	x86_64 znver1
Source0:	ghc-9.14.1-src.tar.xz
Source1:	ghc914-bootstrap-kit.tar.gz
Source2:	ghc914-build.sh
Source3:	%{name}.rpmlintrc

BuildRequires:	ghc912
BuildRequires:	make
BuildRequires:	python
BuildRequires:	perl
BuildRequires:	autoconf
BuildRequires:	patch
BuildRequires:	gcc
BuildRequires:	lld
BuildRequires:	diffutils
BuildRequires:	binutils
BuildRequires:	pkgconfig(gmp)
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	pkgconfig(libffi)
BuildRequires:	pkgconfig(numa)
BuildRequires:	file
BuildRequires:	tar
BuildRequires:	xz
BuildRequires:	gzip

%description
GHC 9.14.1 compiled from its Haskell sources by packaged GHC 9.12.4
(Hadrian, static libraries, host GMP). No upstream bindist and no
GHCup compiler. The build applies the ghci Binary HalfWord guard so
a 9.12.4 boot compiler can build stage-0 ghci.

Installed as ghc914 / ghc-9.14.1 so it can coexist with ghc912 and a
distro GHC.

%prep
set -eu
cd %{_builddir}
rm -rf ghc914-root
mkdir -p ghc914-root
tar -xJf %{SOURCE0} -C ghc914-root
tar -xzf %{SOURCE1} -C ghc914-root
test -d ghc914-root/ghc-9.14.1/hadrian/bootstrap
test "$(tr -d '[:space:]' < ghc914-root/ghc-9.14.1/VERSION)" = "9.14.1"
test -f ghc914-root/bootstrap/plan-bootstrap-9_12_2.json
test -f ghc914-root/bootstrap/ghci-Binary-HalfWord-9.12.3-boot.patch
test -f ghc914-root/bootstrap/regen-parsers.sh
test -f ghc914-root/bootstrap/cmp-regenerated.sh
test -d ghc914-root/bootstrap/hadrian
test -f ghc914-root/bootstrap/happy-1.20.1.1.tar.gz
test -f ghc914-root/bootstrap/alex-3.2.7.4.tar.gz
test -f %{SOURCE2}
set +u

%build
set -eu
bash %{SOURCE2} "%{_builddir}/ghc914-root"
set +u

%install
set -eu
dest=%{_builddir}/ghc914-root/dest
if [ -d "$dest/lib/ghc-9.14.1" ]; then
	src=$dest/lib/ghc-9.14.1
elif [ -d "$dest/lib64/ghc-9.14.1" ]; then
	src=$dest/lib64/ghc-9.14.1
else
	echo "ghc914: install tree has no lib/ghc-9.14.1" >&2
	exit 1
fi
mkdir -p %{buildroot}%{_libdir} %{buildroot}%{_bindir}
cp -a "$src" %{buildroot}%{_libdir}/ghc-9.14.1
test -x %{buildroot}%{_libdir}/ghc-9.14.1/bin/ghc-9.14.1
file %{buildroot}%{_libdir}/ghc-9.14.1/bin/ghc-9.14.1 | grep -q ELF
test -f %{buildroot}%{_libdir}/ghc-9.14.1/lib/settings
test -x %{buildroot}%{_libdir}/ghc-9.14.1/bin/host-gcc
libname=$(basename %{_libdir})
cat > %{buildroot}%{_bindir}/ghc914 << EOF
#!/bin/sh
if [ -x "\$0" ] && [ "\$0" != "\${0#*/}" ]; then
	arg0=\$0
else
	arg0=\$(command -v "\$0") || exit 1
fi
here=\$(CDPATH= cd -- "\$(dirname "\$arg0")" && pwd)
root=\$(dirname "\$here")
exec "\$root/$libname/ghc-9.14.1/bin/ghc-9.14.1" -B"\$root/$libname/ghc-9.14.1/lib" "\$@"
EOF
cat > %{buildroot}%{_bindir}/ghc-pkg914 << EOF
#!/bin/sh
if [ -x "\$0" ] && [ "\$0" != "\${0#*/}" ]; then
	arg0=\$0
else
	arg0=\$(command -v "\$0") || exit 1
fi
here=\$(CDPATH= cd -- "\$(dirname "\$arg0")" && pwd)
root=\$(dirname "\$here")
top="\$root/$libname/ghc-9.14.1"
exec "\$top/bin/ghc-pkg-9.14.1" --global-package-db "\$top/lib/package.conf.d" "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/ghc914 %{buildroot}%{_bindir}/ghc-pkg914
ln -sfn ghc914 %{buildroot}%{_bindir}/ghc-9.14.1
ln -sfn ghc-pkg914 %{buildroot}%{_bindir}/ghc-pkg-9.14.1
set +u

%files
%{_bindir}/ghc914
%{_bindir}/ghc-pkg914
%{_bindir}/ghc-9.14.1
%{_bindir}/ghc-pkg-9.14.1
%{_libdir}/ghc-9.14.1/

%check
set -eu
cd %{_builddir}
export PATH=%{buildroot}%{_bindir}:$PATH
hash -r
command -v ghc914 | grep -q '%{buildroot}'
b=$(command -v ghc914)
g=%{buildroot}%{_libdir}/ghc-9.14.1
test -x "$g/bin/ghc-9.14.1"
file "$g/bin/ghc-9.14.1" | grep -q ELF
test -f "$g/lib/settings"
test -x "$g/bin/host-gcc"
"$b" --numeric-version | tee numeric.out
test "$(cat numeric.out)" = "9.14.1"
"$b" --numeric-version | tee numeric2.out
test "$(cat numeric2.out)" = "9.14.1"
cat > Helper.hs << 'EOF'
module Helper (sumList) where

sumList :: [Int] -> Int
sumList [] = 0
sumList (x:xs) = x + sumList xs
EOF
cat > Main.hs << 'EOF'
module Main where

import Helper

main :: IO ()
main = do
	let xs = [1, 2, 3, 4]
	putStrLn (show (sumList xs))
EOF
rm -rf sum-a sum-b
mkdir sum-a sum-b
cp Helper.hs Main.hs sum-a/
cp Helper.hs Main.hs sum-b/
( cd sum-a && "$b" -v0 --make Main.hs -o sum10 && ./sum10 ) > sum-a.out
test "$(cat sum-a.out)" = "10"
( cd sum-b && "$b" -v0 --make Main.hs -o sum10 && ./sum10 ) > sum-b.out
test "$(cat sum-b.out)" = "10"
set +u
