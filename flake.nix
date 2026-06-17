{
  description = "u4u-engine development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python312;
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          (python.withPackages (ps: with ps; [
            # Testing
            pytest
            responses
            requests
            tenacity

            # Auth
            bcrypt

            # Utilities
            urllib3

            # Database
            psycopg2

            # API surface (required by api.py and engine/users/deps.py;
            # the in-process test suite doesn't spin up uvicorn but does
            # import these modules)
            fastapi
            pydantic
            python-multipart
          ]))
          pkgs.nodejs_20
        ];

        shellHook = ''
          echo "u4u-engine dev shell ready"
          echo "Python: $(python --version)"
        '';
      };
    };
}
