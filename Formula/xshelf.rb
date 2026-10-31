class Xshelf < Formula
  desc "Deterministic runtime tooling for LLM-assisted repository work"
  homepage "https://github.com/fugamante/XSHELF"
  url "https://github.com/fugamante/XSHELF/releases/download/v2026.10.10/SHA256SUMS"
  sha256 "31ee5d6463445406838baa92c4535d0ac049873cd8263ed21cceb6588d451687"
  license "MIT"

  depends_on macos: :sequoia

  resource "release" do
    on_arm do
      url "https://github.com/fugamante/XSHELF/releases/download/v2026.10.10/xshelf-2026.10.10-aarch64-apple-darwin.tar.gz"
      sha256 "2a621c9dd3fc932ac380657f0153888c2c8a977a164726c1e0903bcede6e8e5b"
    end

    on_intel do
      url "https://github.com/fugamante/XSHELF/releases/download/v2026.10.10/xshelf-2026.10.10-x86_64-apple-darwin.tar.gz"
      sha256 "66999b0eac363095b029c76c712eba5737f2f79355133e56493dcff4896cf66c"
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
    assert_match '"version": "2026.10.10"', version_output
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
