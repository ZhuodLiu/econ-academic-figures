// Rasterise every page of a PDF to PNG (macOS, no extra installs): swift pdf2png.swift in.pdf outdir [scale]
import Foundation
import PDFKit
import AppKit

let args = CommandLine.arguments
guard args.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
    print("usage: pdf2png in.pdf outdir [scale]"); exit(1)
}
let outDir = args[2]
let scale = CGFloat(Double(args.count > 3 ? args[3] : "1.5") ?? 1.5)
for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { continue }
    let rect = page.bounds(for: .mediaBox)
    let w = Int(rect.width * scale), h = Int(rect.height * scale)
    guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                              space: CGColorSpaceCreateDeviceRGB(),
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { continue }
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: ctx)
    guard let img = ctx.makeImage(),
          let data = NSBitmapImageRep(cgImage: img).representation(using: .png, properties: [:]) else { continue }
    try? data.write(to: URL(fileURLWithPath: String(format: "%@/page-%02d.png", outDir, i + 1)))
}
print("pages:", doc.pageCount)
