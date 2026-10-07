class Xshelf < Formula
  desc "Deterministic runtime tooling for LLM-assisted repository work"
  homepage "https://github.com/fugamante/XSHELF"
  url "https://github.com/fugamante/XSHELF/releases/download/v2026.10.07/SHA256SUMS"
  sha256 "1b2ff930dd89ea35538ee571189d0bd7b29647c059e525660be609f26326ff9c"
  license "MIT"

  depends_on macos: :sequoia

  resource "release" do
    on_arm do
      url "https://github.com/fugamante/XSHELF/releases/download/v2026.10.07/xshelf-2026.10.07-aarch64-apple-darwin.tar.gz"
      sha256 "db276dab7662bfbc58ff79968b6c4e9bd3295456d66c858bc93758267ef0b5b1"
    end

    on_intel do
      url "https://github.com/fugamante/XSHELF/releases/download/v2026.10.07/xshelf-2026.10.07-x86_64-apple-darwin.tar.gz"
      sha256 "27af439a84495e6d68e127df5ba1dabaeaebe3593b28497b606abb246fc6686d"
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
    assert_match '"version": "2026.10.07"', version_output
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
