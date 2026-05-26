{
  description = "Python environment for testing u4u-engine";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    pythonEnv = pkgs.python3.withPackages (ps: with ps; [
      pytest
      responses
      requests
      pysam
      fastapi
      uvicorn
      tenacity
    ]);
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [
        pythonEnv
      ];
    };
  };
}
