with import <nixpkgs> { };
mkShell {
  nativeBuildInputs = [
    python313
    python313Packages.requests
    python313Packages.types-requests
    python313Packages.cbor2
    python313Packages.tqdm
    python313Packages.types-tqdm
    python313Packages.pandas
    python313Packages.weasyprint
    noto-fonts
  ];
}
