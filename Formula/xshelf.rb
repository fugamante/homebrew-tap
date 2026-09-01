class Xshelf < Formula
  desc "Deterministic runtime tooling for LLM-assisted repository work"
  homepage "https://github.com/fugamante/XSHELF"
  url "https://github.com/fugamante/XSHELF/releases/download/v2026.08.29/SHA256SUMS"
  sha256 "dc8cfa754c7024ea88d7f9e6c39d2993c5e3672ef71313ac9307f3cfcab9407e"
  license "MIT"
  revision 1

  bottle do
    root_url "https://ghcr.io/v2/fugamante/tap"
    sha256 cellar: :any_skip_relocation, arm64_sequoia: "238df327ac156bc2b4c214b9368722a6cdc342a4e00d9e66b9ee56a5417923fb"
    sha256 cellar: :any_skip_relocation, sequoia:       "63941eb9caa1cbf8472e6baafa22241db5418765bfb43bf600bd949c622d3aa1"
  end
  depends_on macos: :sequoia

  resource "release" do
    on_arm do
      url "https://github.com/fugamante/XSHELF/releases/download/v2026.08.29/xshelf-2026.08.29-aarch64-apple-darwin.tar.gz"
      sha256 "8805b084205cbb5641cdd95099d5bffa615ca9d68f80a7823a4277b3279d0a23"
    end

    on_intel do
      url "https://github.com/fugamante/XSHELF/releases/download/v2026.08.29/xshelf-2026.08.29-x86_64-apple-darwin.tar.gz"
      sha256 "86a4539e93d721a25ee959d802010f2c3897b84538237a63f75ae358b21a9e9c"
    end
  end

  def install
    resource("release").stage do
      bin.install "bin/xshelf"
      bin.install_symlink "xshelf" => "xs"
      bin.install_symlink "xshelf" => "cx"
      pkgshare.install "share/xshelf/schemas"
      man1.install "share/man/man1/xshelf.1"
      man1.install "share/man/man1/xs.1"
      man1.install "share/man/man1/cx.1"
      doc.install "README.md", "LICENSE"
    end
  end

  test do
    version_output = shell_output("#{bin}/xshelf version --json")
    assert_match '"contract_version": "version.v1"', version_output
    assert_match '"version": "2026.08.29"', version_output
    assert_predicate bin/"xs", :executable?
    assert_predicate bin/"cx", :executable?
    assert_path_exists man1/"xshelf.1"
    assert_path_exists man1/"xs.1"
    assert_path_exists man1/"cx.1"
    assert_path_exists pkgshare/"schemas/commitjson.schema.json"
    assert_path_exists pkgshare/"schemas/diffsum.schema.json"
    assert_path_exists pkgshare/"schemas/fixrun.schema.json"
    assert_path_exists pkgshare/"schemas/next.schema.json"
    assert_match "\n  xs <command>", shell_output("#{bin}/xs help")
    assert_match "\n  cx <command>", shell_output("#{bin}/cx help")
    schema_output = shell_output("#{bin}/xshelf schema list --json")
    assert_match '"file_count":4', schema_output.delete(" ")
    contract_output = shell_output("#{bin}/xshelf contracts validate --profile eval-lab --json")
    assert_match '"ok": true', contract_output
  end
end
